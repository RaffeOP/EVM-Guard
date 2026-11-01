pragma solidity 0.5.12;

contract Wallet7579 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        total += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }

    function totalDeposits() public view returns (uint256) { return total; }
}
