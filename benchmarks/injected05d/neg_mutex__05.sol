pragma solidity 0.5.12;

contract Wallet3928 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        balances[msg.sender] -= amount;
        reserve -= amount;
        locked = false;
    }
}
