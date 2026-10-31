pragma solidity 0.5.12;

contract Vault3980 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        total += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }

    function totalDeposits() public view returns (uint256) { return total; }
}
