pragma solidity 0.8.20;

contract Escrow9611 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        credit[msg.sender] -= amount;
        supply -= amount;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
